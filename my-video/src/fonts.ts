import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadMono } from '@remotion/google-fonts/JetBrainsMono';
import { loadFont as loadBrand } from '@remotion/google-fonts/PlusJakartaSans';

const { fontFamily: fontSans } = loadInter('normal', {
  weights: ['400', '500', '600'],
  subsets: ['latin'],
});

const { fontFamily: fontMono } = loadMono('normal', {
  weights: ['400', '500', '600'],
  subsets: ['latin'],
});

const { fontFamily: fontBrand } = loadBrand('normal', {
  weights: ['500', '600', '700'],
  subsets: ['latin'],
});

export const F = {
  sans: fontSans,
  mono: fontMono,
  brand: fontBrand,
} as const;
