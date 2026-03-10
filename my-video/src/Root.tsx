import './index.css';
import './fonts'; // load fonts early
import { Composition, Folder } from 'remotion';
import { HelloWorld, myCompSchema } from './HelloWorld';
import { Logo, myCompSchema2 } from './HelloWorld/Logo';
import { ChandelierDemo } from './ChandelierDemo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ── chandelierp demo reel ── */}
      <Folder name="Chandelier">
        <Composition
          id="ChandelierReel"
          component={ChandelierDemo}
          durationInFrames={975}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>

      {/* ── original Remotion starter (keep for reference) ── */}
      <Folder name="Starter">
        <Composition
          id="HelloWorld"
          component={HelloWorld}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          schema={myCompSchema}
          defaultProps={{
            titleText: 'Welcome to Remotion',
            titleColor: '#000000',
            logoColor1: '#91EAE4',
            logoColor2: '#86A8E7',
          }}
        />
        <Composition
          id="OnlyLogo"
          component={Logo}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          schema={myCompSchema2}
          defaultProps={{
            logoColor1: '#91dAE2' as const,
            logoColor2: '#86A8E7' as const,
          }}
        />
      </Folder>
    </>
  );
};
