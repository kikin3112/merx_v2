import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { VideoEmbed } from './components/VideoEmbed';
import { Pricing } from './components/Pricing';
import { Footer } from './components/Footer';

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Features />
        <VideoEmbed />
        <Pricing />
      </main>
      <Footer />
    </>
  );
}
