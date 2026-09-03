const { withAndroidManifest } = require('@expo/config-plugins');

const PACKAGES = [
  'com.grofers.customerapp',
  'com.zeptoconsumerapp',
  'in.swiggy.android',
  'com.bigbasket.mobileapp',
  'com.flipkart.android',
  'in.amazon.mShop.android.shopping',
];

module.exports = function withAndroidPackageQueries(config) {
  return withAndroidManifest(config, config => {
    const manifest = config.modResults.manifest;
    manifest.queries = manifest.queries || [];

    for (const packageName of PACKAGES) {
      const exists = manifest.queries.some(entry =>
        Array.isArray(entry.package) &&
        entry.package.some(item => item.$?.['android:name'] === packageName)
      );
      if (!exists) {
        manifest.queries.push({ package: [{ $: { 'android:name': packageName } }] });
      }
    }

    return config;
  });
};
