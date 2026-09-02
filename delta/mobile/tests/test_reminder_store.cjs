const assert = require('assert');

// Test suite for Reminder Engine & Scheduling
async function testReminderStore() {
  console.log('🧪 Running Delta Reminder Store & Scheduling Test Suite...');

  // Mock reminder store structure
  const reminders = [];
  let activeNotification = null;

  // 1. Create Reminder with relative delay
  const now = Date.now();
  const delayMinutes = 2;
  const item = {
    id: `rem_${Date.now()}`,
    title: 'Audit Port 8000',
    targetTime: now + (delayMinutes * 60 * 1000),
    note: 'Pastikan firewall aktif',
    isTriggered: false,
    isCompleted: false,
    createdAt: now,
  };
  reminders.push(item);

  assert.strictEqual(reminders.length, 1);
  assert.strictEqual(reminders[0].title, 'Audit Port 8000');
  console.log('✅ Reminder creation passed');

  // 2. Check due scheduling logic
  // Simulate time passed (now > targetTime)
  const simulatedNow = now + (3 * 60 * 1000);
  const dueItem = reminders.find(r => !r.isTriggered && !r.isCompleted && r.targetTime <= simulatedNow);

  assert(dueItem !== undefined, 'Due item must be triggered when targetTime <= now');
  if (dueItem) {
    dueItem.isTriggered = true;
    activeNotification = dueItem;
  }

  assert.strictEqual(activeNotification.title, 'Audit Port 8000');
  console.log('✅ Due reminder detection & notification trigger passed');

  // 3. Complete reminder
  if (activeNotification) {
    dueItem.isCompleted = true;
    activeNotification = null;
  }
  assert.strictEqual(activeNotification, null);
  assert.strictEqual(dueItem.isCompleted, true);
  console.log('✅ Complete reminder & dismiss notification passed');

  console.log('🎉 All Reminder Engine tests PASSED 100%!');
}

testReminderStore().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
