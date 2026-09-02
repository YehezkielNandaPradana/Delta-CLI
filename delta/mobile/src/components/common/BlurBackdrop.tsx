import React from 'react';
import { StyleSheet, View, Platform, ViewStyle } from 'react-native';

interface BlurBackdropProps {
  intensity?: number;
  style?: ViewStyle | ViewStyle[];
  children?: React.ReactNode;
}

export const BlurBackdrop: React.FC<BlurBackdropProps> = ({
  intensity = 35,
  style,
  children,
}) => {
  let BlurViewComponent: any = null;
  try {
    const ExpoBlur = require('expo-blur');
    BlurViewComponent = ExpoBlur.BlurView;
  } catch (_) {
    BlurViewComponent = null;
  }

  if (BlurViewComponent && Platform.OS !== 'web') {
    return (
      <BlurViewComponent
        intensity={intensity}
        tint="dark"
        style={[styles.absolute, style]}
      >
        {children}
      </BlurViewComponent>
    );
  }

  // Pure clean fallback overlay
  return (
    <View style={[styles.fallback, style]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  absolute: {
    ...StyleSheet.absoluteFillObject,
  },
  fallback: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
  },
});
