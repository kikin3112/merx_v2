import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { Testimonials } from './components/Testimonials';
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
        <Testimonials />
        <VideoEmbed />
        <Pricing />
      </main>
      <Footer />
    </>
  );
}
