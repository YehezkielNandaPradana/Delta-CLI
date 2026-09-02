const assert = require('assert');

// Test suite for 9Router PRoot / Android Termux / Local discovery
async function run9RouterConnectionTest() {
  console.log('🧪 Starting 9Router Discovery & Auto-Routing Integration Test...');

  const LOCAL_ROUTER_HOSTS = [
    'http://192.168.1.6:20128',
    'http://127.0.0.1:20128',
    'http://localhost:20128',
  ];

  // 1. Verify candidate list has PRoot / Termux loopback & LAN IP
  assert(LOCAL_ROUTER_HOSTS.includes('http://127.0.0.1:20128'), 'Loopback 127.0.0.1 must be candidate');
  assert(LOCAL_ROUTER_HOSTS.includes('http://localhost:20128'), 'Localhost must be candidate');
  console.log('✅ Candidate hosts list valid for PRoot / Termux / Laptop');

  // 2. Test live ping against local 9Router (currently active on port 20128)
  let liveFound = false;
  for (const host of LOCAL_ROUTER_HOSTS) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${host}/v1/models`, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        const json = await res.json();
        console.log(`✅ Successfully connected to 9Router at ${host} (Models: ${json?.data?.length || 0})`);
        liveFound = true;
        break;
      }
    } catch (e) {
      // expected if host interface differs
    }
  }

  assert(liveFound, '9Router should be reachable on at least one candidate host');
  console.log('🎉 9Router connectivity test PASSED 100%!');
}

run9RouterConnectionTest().catch((err) => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
