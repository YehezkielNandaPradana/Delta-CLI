export interface ReminderItem {
  id: string;
  title: string;
  targetTime: number; // timestamp in ms
  note?: string;
  isTriggered: boolean;
  isCompleted: boolean;
  createdAt: number;
}
