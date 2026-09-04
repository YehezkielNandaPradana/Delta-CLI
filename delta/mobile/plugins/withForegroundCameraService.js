const { withAndroidManifest, withMainApplication } = require('@expo/config-plugins');
const fs = require('fs');
const path = require('path');

/**
 * Expo Config Plugin to inject:
 * 1. Android Foreground Service declarations compliant with Android 14+ (API 34)
 * 2. Native Java Source files into android/app/src/main/java/com/deltasec/mobile/service/
 * 3. Registration of CameraForegroundPackage in MainApplication
 */
function withForegroundCameraService(config) {
  // 1. Android Manifest Service injection
  config = withAndroidManifest(config, async (config) => {
    const androidManifest = config.modResults;
    const application = androidManifest.manifest.application?.[0];

    if (!application) return config;

    if (!application.service) {
      application.service = [];
    }

    const serviceName = 'com.deltasec.mobile.service.CameraMonitoringForegroundService';
    const existingService = application.service.find(
      (s) => s.$?.['android:name'] === serviceName
    );

    if (!existingService) {
      application.service.push({
        $: {
          'android:name': serviceName,
          'android:enabled': 'true',
          'android:exported': 'false',
          'android:foregroundServiceType': 'camera',
          'android:stopWithTask': 'true',
        },
      });
    } else {
      existingService.$['android:foregroundServiceType'] = 'camera';
      existingService.$['android:stopWithTask'] = 'true';
    }

    return config;
  });

  // 2. Inject Native Java source files and register package in MainApplication
  config = withMainApplication(config, async (config) => {
    const projectRoot = config.modRequest.projectRoot;
    const platformProjectRoot = config.modRequest.platformProjectRoot;

    // Target directory: android/app/src/main/java/com/deltasec/mobile/service/
    const targetDir = path.join(
      platformProjectRoot,
      'app',
      'src',
      'main',
      'java',
      'com',
      'deltasec',
      'mobile',
      'service'
    );

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const sourceDir = path.join(projectRoot, 'plugins', 'android');
    const javaFiles = [
      'CameraMonitoringForegroundService.java',
      'CameraForegroundModule.java',
      'CameraForegroundPackage.java',
    ];

    for (const file of javaFiles) {
      const src = path.join(sourceDir, file);
      const dest = path.join(targetDir, file);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, dest);
      }
    }

    // Register CameraForegroundPackage in MainApplication
    let mainAppContent = config.modResults.contents;

    // Fix: Package declaration must remain at the very top before any imports
    const packageImport = 'import com.deltasec.mobile.service.CameraForegroundPackage;';
    if (!mainAppContent.includes(packageImport)) {
      if (mainAppContent.includes('package com.deltasec.mobile')) {
        mainAppContent = mainAppContent.replace(
          'package com.deltasec.mobile',
          'package com.deltasec.mobile\n\n' + packageImport
        );
      } else {
        mainAppContent = packageImport + '\n' + mainAppContent;
      }
    }

    // Kotlin getPackages syntax: PackageList(this).packages.apply { add(...) } or mutable list
    if (!mainAppContent.includes('CameraForegroundPackage()')) {
      if (mainAppContent.includes('PackageList(this).packages')) {
        mainAppContent = mainAppContent.replace(
          'PackageList(this).packages',
          'PackageList(this).packages.toMutableList().apply { add(CameraForegroundPackage()) }'
        );
      }
    }

    config.modResults.contents = mainAppContent;
    return config;
  });

  return config;
}

module.exports = withForegroundCameraService;
