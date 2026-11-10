import React from 'react';
import {Composition} from 'remotion';
import plan from './data/plan.json';
import {UniversalReel} from './renderer/UniversalReel';

const safeDuration = Math.max(30, Number(plan.total_duration_frames || 2100));

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Reel"
      component={UniversalReel}
      durationInFrames={safeDuration}
      fps={Number(plan.fps || 30)}
      width={Number(plan.width || 1080)}
      height={Number(plan.height || 1920)}
      defaultProps={{plan}}
    />
  );
};
