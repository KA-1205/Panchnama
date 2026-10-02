/**
 * App root (Panchnama AI Media Intelligence Platform - Capture App).
 * Bootstraps the native capture runtime, registers sync triggers, loads the
 * org's real & demo inspection projects, supports member authentication,
 * and renders screens themed with the official Panchnama AI color palette.
 */
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { CAPTURE_APP_VERSION } from './src/index.js';
import { CameraScreen } from './src/screens/CameraScreen.js';
import { ProjectPickerScreen } from './src/screens/ProjectPickerScreen.js';
import { QueueScreen } from './src/screens/QueueScreen.js';
import { LoginScreen } from './src/screens/LoginScreen.js';
import { createCaptureRuntime, registerSyncTriggers, type CaptureRuntime } from './src/native/index.js';
import { getSessionToken, clearSessionToken } from './src/native/session.js';
import { fetchProjects } from './src/api.js';
import { colors } from './src/theme.js';
import type { CaptureSelection } from './src/projects.js';
import type { Project } from '@panchnama/shared/rn';

type Screen = 'login' | 'picker' | 'camera' | 'queue';

/**
 * Real inspection projects suite for Panchnama AI field workers across multiple sectors.
 */
const REAL_DEMO_PROJECTS: Project[] = [
  {
    id: '00000000-0000-4000-8000-000000000001',
    org_id: '00000000-0000-4000-8000-0000000000aa',
    name: 'Riverside Reforestation & Bio-Shield',
    config: {
      observation_types: [
        { type: 'sapling_survival', label: 'Sapling Survival Audit', model: 'forestry_v1', gps_radius: 25 },
        { type: 'canopy_cover', label: 'Canopy Density Check', model: 'forestry_v1', gps_radius: 50 },
      ],
    },
    parent_project_id: null,
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-4000-8000-000000000002',
    org_id: '00000000-0000-4000-8000-0000000000aa',
    name: 'North Zone Planting Plot A (Sub-project)',
    config: { observation_types: [] },
    parent_project_id: '00000000-0000-4000-8000-000000000001',
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-4000-8000-000000000003',
    org_id: '00000000-0000-4000-8000-0000000000aa',
    name: 'Sundarbans Coastal Mangrove Protection',
    config: {
      observation_types: [
        { type: 'mangrove_health', label: 'Mangrove Density & Health', model: 'wetlands_v1', gps_radius: 30 },
        { type: 'soil_erosion', label: 'Tidal Bank Soil Erosion', model: 'erosion_v1', gps_radius: 20 },
      ],
    },
    parent_project_id: null,
    created_at: new Date().toISOString(),
  },
  {
    id: '00000000-0000-4000-8000-000000000004',
    org_id: '00000000-0000-4000-8000-0000000000aa',
    name: 'Thar Solar Infrastructure & Array Audit',
    config: {
      observation_types: [
        { type: 'solar_panel_defect', label: 'PV Thermal & Defect Audit', model: 'solar_v1', gps_radius: 15 },
      ],
    },
    parent_project_id: null,
    created_at: new Date().toISOString(),
  },
];

async function loadProjects(token: string | null): Promise<Project[]> {
  if (process.env.EXPO_PUBLIC_DEV_SEED === '1') return REAL_DEMO_PROJECTS;
  if (!token) return REAL_DEMO_PROJECTS;

  const base = process.env.EXPO_PUBLIC_API_URL;
  if (!base) return REAL_DEMO_PROJECTS;

  try {
    return await fetchProjects({ baseUrl: base, token });
  } catch {
    return REAL_DEMO_PROJECTS;
  }
}

export default function App(): JSX.Element {
  const [runtime, setRuntime] = useState<CaptureRuntime | null>(null);
  const [projects, setProjects] = useState<readonly Project[]>([]);
  const [selection, setSelection] = useState<CaptureSelection | null>(null);
  const [screen, setScreen] = useState<Screen>('picker');
  const [sessionToken, setSessionTokenState] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>('member@panchnama.ai');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let unsubscribe: (() => void) | undefined;
    (async () => {
      try {
        const rt = await createCaptureRuntime();
        setRuntime(rt);
        unsubscribe = await registerSyncTriggers(rt);

        const token = await getSessionToken();
        setSessionTokenState(token);
        if (!token) {
          setScreen('login');
        }
        setProjects(await loadProjects(token));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => unsubscribe?.();
  }, []);

  const handleLogout = async () => {
    await clearSessionToken();
    setSessionTokenState(null);
    setUserEmail(null);
    setScreen('login');
  };

  const handleLoginSuccess = async (token: string, email: string) => {
    setSessionTokenState(token);
    setUserEmail(email);
    setProjects(await loadProjects(token));
    setScreen('picker');
  };

  if (error !== null) {
    return (
      <View style={styles.center}>
        <StatusBar style="dark" />
        <Text style={styles.errorHeader}>Startup Error</Text>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  if (runtime === null) {
    return (
      <View style={styles.center}>
        <StatusBar style="dark" />
        <ActivityIndicator size="large" color={colors.brandPrimary} />
        <Text style={styles.loadingText}>Starting Panchnama Capture {CAPTURE_APP_VERSION}…</Text>
      </View>
    );
  }

  const orgId = process.env.EXPO_PUBLIC_ORG_ID ?? '00000000-0000-4000-8000-0000000000aa';

  const SCREEN_ICONS: Record<Screen, string> = {
    login: '🔑',
    picker: '📋',
    camera: '📷',
    queue: '⚡',
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />

      {/* Top App Bar Header */}
      <View style={styles.headerBar}>
        <View>
          <Text style={styles.headerBrand}>Panchnama AI</Text>
          <Text style={styles.headerSub}>
            {sessionToken && userEmail ? `👤 ${userEmail} (Member)` : 'Media Intelligence Platform'}
          </Text>
        </View>
        {sessionToken ? (
          <Pressable style={styles.logoutChip} onPress={() => void handleLogout()}>
            <Text style={styles.logoutChipText}>Log Out</Text>
          </Pressable>
        ) : (
          <View style={styles.guestChip}>
            <Text style={styles.guestChipText}>Demo Mode</Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        {screen === 'login' && (
          <LoginScreen
            initialEmail={userEmail}
            onLoginSuccess={(token, email) => void handleLoginSuccess(token, email)}
          />
        )}
        {screen === 'picker' && (
          <ProjectPickerScreen
            projects={projects}
            onSelected={(s) => {
              setSelection(s);
              setScreen('camera');
            }}
          />
        )}
        {screen === 'camera' && selection !== null && (
          <CameraScreen
            runtime={runtime}
            selection={selection}
            orgId={orgId}
            appVersion={CAPTURE_APP_VERSION}
            onCaptured={() => setScreen('queue')}
          />
        )}
        {screen === 'queue' && <QueueScreen runtime={runtime} />}
      </View>

      {/* Navigation Tab Bar */}
      <View style={styles.tabbar}>
        {(['login', 'picker', 'camera', 'queue'] as Screen[]).map((s) => {
          const isActive = s === screen;
          return (
            <Pressable key={s} style={styles.tabItem} onPress={() => setScreen(s)}>
              <Text style={styles.tabIcon}>{SCREEN_ICONS[s]}</Text>
              <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                {s}
              </Text>
              {isActive && <View style={styles.tabActiveIndicator} />}
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background, paddingTop: 40 },
  content: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, backgroundColor: colors.background },
  loadingText: { color: colors.textSecondary, marginTop: 12, fontSize: 14, fontWeight: '500' },
  errorHeader: { color: colors.error, fontSize: 18, fontWeight: '800', marginBottom: 8 },
  error: { color: colors.textSecondary, textAlign: 'center', fontSize: 13 },
  
  headerBar: {
    height: 54,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerBrand: { fontSize: 16, fontWeight: '800', color: colors.textPrimary },
  headerSub: { fontSize: 11, color: colors.brandSecondary, fontWeight: '600', marginTop: 1 },

  logoutChip: {
    backgroundColor: colors.elevated,
    borderColor: colors.border,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  logoutChipText: { color: colors.error, fontSize: 11, fontWeight: '700' },

  guestChip: {
    backgroundColor: colors.softAccent,
    borderColor: colors.border,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  guestChipText: { color: colors.brandPrimary, fontSize: 11, fontWeight: '700' },

  tabbar: {
    height: 60,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  tabItem: { alignItems: 'center', justifyContent: 'center', flex: 1, height: '100%' },
  tabIcon: { fontSize: 16 },
  tabLabel: { color: colors.textMuted, fontSize: 11, fontWeight: '600', textTransform: 'capitalize', marginTop: 2 },
  tabLabelActive: { color: colors.brandPrimary, fontWeight: '800' },
  tabActiveIndicator: {
    position: 'absolute',
    bottom: 4,
    width: 6,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.brandPrimary,
  },
});
