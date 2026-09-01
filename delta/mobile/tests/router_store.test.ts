import { useConnectionStore } from '../src/store/useConnectionStore';

describe('useConnectionStore - Router State', () => {
  beforeEach(() => {
    useConnectionStore.setState({ isRouterRunning: true });
  });

  it('updates router running status', () => {
    useConnectionStore.getState().setIsRouterRunning(false);
    expect(useConnectionStore.getState().isRouterRunning).toBe(false);
  });
});
