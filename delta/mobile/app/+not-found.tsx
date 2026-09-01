import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Link } from 'expo-router';
import { COLORS } from '../src/theme/colors';

export default function NotFoundScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>This screen doesn't exist.</Text>
      <Link href="/" asChild>
        <TouchableOpacity style={styles.link}>
          <Text style={styles.linkText}>Go to home screen</Text>
        </TouchableOpacity>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: COLORS.bgPrimary,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 16,
  },
  link: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: COLORS.bgCard,
    borderRadius: 8,
  },
  linkText: {
    fontSize: 14,
    color: COLORS.accentGreen,
    fontWeight: '600',
  },
});
