import React from 'react';
import { Tabs } from 'expo-router';
import { FluidBottomBar } from '../../src/components/common/FluidBottomBar';
import { useThemeColors } from '../../src/theme/theme';

export default function TabLayout() {
  const { colors } = useThemeColors();

  return (
    <Tabs
      tabBar={(props) => <FluidBottomBar {...props} />}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Chat',
        }}
      />
      <Tabs.Screen
        name="activity"
        options={{
          title: 'Activity',
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'History',
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
        }}
      />
    </Tabs>
  );
}
