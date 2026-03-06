import type { Metadata } from 'next';
import Link from 'next/link';
import { getAllPosts } from '@/lib/blog';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';

export const metadata: Metadata = {
  title: 'Blog — chandelierp',
  description: 'Artículos sobre candelería, gestión de PyMEs y novedades de chandelierp.',
};

export default function BlogPage() {
  const posts = getAllPosts();

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-cream">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
              Blog
            </h1>
            <p className="mt-4 text-lg text-gray-500">
              Noticias, consejos y novedades del mundo de la candelería.
            </p>
          </div>

          {/* Posts list */}
          {posts.length === 0 ? (
            <p className="text-center text-gray-400">
              Aún no hay artículos publicados. Vuelve pronto.
            </p>
          ) : (
            <div className="space-y-8">
              {posts.map((post) => (
                <article
                  key={post.slug}
                  className="bg-white rounded-2xl border border-gray-100 p-6 sm:p-8 hover:border-amber-200 hover:shadow-md transition-all"
                >
                  <Link href={`/blog/${post.slug}`} className="block group">
                    <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
                      <time dateTime={post.date}>{post.date}</time>
                      <span>&middot;</span>
                      <span>{post.author}</span>
                    </div>
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 group-hover:text-amber-600 transition-colors">
                      {post.title}
                    </h2>
                    <p className="mt-3 text-gray-500 leading-relaxed">
                      {post.excerpt}
                    </p>
                    <span className="mt-4 inline-block text-amber-600 font-medium text-sm group-hover:underline">
                      Leer más &rarr;
                    </span>
                  </Link>
                </article>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
