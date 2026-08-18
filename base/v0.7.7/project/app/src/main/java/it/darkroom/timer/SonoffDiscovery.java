package it.darkroom.timer;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.net.wifi.WifiManager;
import android.os.Handler;
import android.os.Looper;

import java.lang.reflect.Method;
import java.net.InetAddress;
import java.util.ArrayDeque;
import java.util.Map;

/**
 * Discovers all SONOFF devices advertised as _ewelink._tcp and distinguishes
 * DIY candidates from encrypted eWeLink LAN mode.
 *
 * Resolution is deliberately serialized: Android's legacy NSD resolver can
 * reject overlapping resolveService() calls on some devices/OS versions.
 */
public final class SonoffDiscovery {
    public interface Listener {
        void onSearching();
        void onDiyCandidate(DeviceConfig device, String type, String apiVersion);
        void onEwelinkMode(String host, int port, String deviceId, String type);
        void onError(String message);
    }

    private static final String TYPE = "_ewelink._tcp.";
    private final Context context;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Object queueLock = new Object();
    private final ArrayDeque<NsdServiceInfo> resolveQueue = new ArrayDeque<>();

    private NsdManager nsd;
    private NsdManager.DiscoveryListener discovery;
    private WifiManager.MulticastLock multicastLock;
    private boolean resolving;
    private boolean stopped;

    public SonoffDiscovery(Context context, Listener listener) {
        this.context = context.getApplicationContext();
        this.listener = listener;
    }

    public void start() {
        stop();
        stopped = false;
        main.post(listener::onSearching);

        WifiManager wifi = (WifiManager) context.getSystemService(Context.WIFI_SERVICE);
        if (wifi != null) {
            multicastLock = wifi.createMulticastLock("darkroom-sonoff-mdns");
            multicastLock.setReferenceCounted(false);
            try { multicastLock.acquire(); } catch (Exception ignored) {}
        }

        nsd = (NsdManager) context.getSystemService(Context.NSD_SERVICE);
        discovery = new NsdManager.DiscoveryListener() {
            @Override public void onDiscoveryStarted(String serviceType) {}
            @Override public void onDiscoveryStopped(String serviceType) {}

            @Override public void onStartDiscoveryFailed(String serviceType, int errorCode) {
                main.post(() -> listener.onError("Ricerca LAN non avviata (" + errorCode + ")"));
            }

            @Override public void onStopDiscoveryFailed(String serviceType, int errorCode) {}

            @Override public void onServiceFound(NsdServiceInfo serviceInfo) {
                String t = serviceInfo.getServiceType();
                if (t == null || !t.contains("_ewelink._tcp")) return;
                enqueueResolve(serviceInfo);
            }

            @Override public void onServiceLost(NsdServiceInfo serviceInfo) {}
        };

        try {
            nsd.discoverServices(TYPE, NsdManager.PROTOCOL_DNS_SD, discovery);
        } catch (Exception e) {
            main.post(() -> listener.onError("Errore ricerca LAN: " + e.getMessage()));
        }
    }

    private void enqueueResolve(NsdServiceInfo serviceInfo) {
        synchronized (queueLock) {
            if (stopped) return;
            resolveQueue.add(serviceInfo);
            if (!resolving) resolveNextLocked();
        }
    }

    private void resolveNextLocked() {
        if (stopped || nsd == null || resolving) return;
        NsdServiceInfo next = resolveQueue.poll();
        if (next == null) return;
        resolving = true;

        try {
            nsd.resolveService(next, new NsdManager.ResolveListener() {
                @Override public void onResolveFailed(NsdServiceInfo serviceInfo, int errorCode) {
                    finishResolve();
                }

                @Override public void onServiceResolved(NsdServiceInfo resolved) {
                    try {
                        String id = readAttr(resolved, "id");
                        if (id.isEmpty()) id = deriveId(resolved.getServiceName());
                        String host = chooseHost(resolved);
                        int port = resolved.getPort();
                        String localType = readAttr(resolved, "type");
                        String apiVersion = readAttr(resolved, "apivers");
                        String encrypted = readAttr(resolved, "encrypt");

                        if (!id.isEmpty() && !host.isEmpty() && port > 0) {
                            boolean looksEncrypted = "true".equalsIgnoreCase(encrypted) || "1".equals(encrypted);
                            if (!looksEncrypted) {
                                DeviceConfig d = new DeviceConfig(host, port, id);
                                main.post(() -> listener.onDiyCandidate(d, localType, apiVersion));
                            } else {
                                final String shownType = localType.isEmpty() ? "eWeLink" : localType;
                                final String shownId = id;
                                main.post(() -> listener.onEwelinkMode(host, port, shownId, shownType));
                            }
                        }
                    } catch (Exception ignored) {
                    } finally {
                        finishResolve();
                    }
                }
            });
        } catch (Exception e) {
            resolving = false;
            resolveNextLocked();
        }
    }

    private void finishResolve() {
        synchronized (queueLock) {
            resolving = false;
            resolveNextLocked();
        }
    }

    @SuppressWarnings("unchecked")
    private static String readAttr(NsdServiceInfo info, String key) {
        try {
            Method m = info.getClass().getMethod("getAttributes");
            Map<String, byte[]> attrs = (Map<String, byte[]>) m.invoke(info);
            byte[] v = attrs == null ? null : attrs.get(key);
            return v == null ? "" : new String(v, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    private static String chooseHost(NsdServiceInfo info) {
        try {
            InetAddress a = info.getHost();
            return a == null ? "" : a.getHostAddress();
        } catch (Exception e) {
            return "";
        }
    }

    private static String deriveId(String serviceName) {
        if (serviceName == null) return "";
        String s = serviceName.trim();
        int p = s.toLowerCase().indexOf("ewelink_");
        if (p >= 0) return s.substring(p + 8).replaceAll("[^A-Za-z0-9]", "");
        if (s.matches("[A-Za-z0-9]{8,20}")) return s;
        return "";
    }

    public void stop() {
        stopped = true;
        synchronized (queueLock) {
            resolveQueue.clear();
            resolving = false;
        }
        if (nsd != null && discovery != null) {
            try { nsd.stopServiceDiscovery(discovery); } catch (Exception ignored) {}
        }
        discovery = null;
        nsd = null;
        if (multicastLock != null) {
            try { if (multicastLock.isHeld()) multicastLock.release(); } catch (Exception ignored) {}
        }
        multicastLock = null;
    }
}
