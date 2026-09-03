import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { describe, expect, it, jest } from '@jest/globals';

import { stateKindForError, SystemState } from '../SystemState';
import { ApiError } from '../../api/client';

jest.mock('../../accessibility/ExperienceContext', () => ({ useExperience: () => ({ reduceMotion: true }) }));

describe('SystemState', () => {
  it('renders an accessible partial-provider state and retry action', async () => {
    const retry = jest.fn();
    const screen = await render(<SystemState kind="partial" actionLabel="Try again" onAction={retry} />);
    expect(screen.getByText('Some results are unavailable')).toBeTruthy();
    fireEvent.press(screen.getByText('Try again'));
    expect(retry).toHaveBeenCalledTimes(1);
  }, 15_000);

  it('maps network and quota errors without exposing implementation details', () => {
    expect(stateKindForError(new ApiError('offline', 0))).toBe('offline');
    expect(stateKindForError(new ApiError('quota', 429, 'quota_exhausted'))).toBe('quota_exhausted');
  });
});
