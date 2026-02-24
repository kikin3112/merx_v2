import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { MDXRemote } from 'next-mdx-remote/rsc';
import { getAllPosts, getPostBySlug } from '@/lib/blog';
import { Navbar } from '../../components/Navbar';
import { Footer } from '../../components/Footer';

interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const posts = getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = getPostBySlug(slug);
  if (!post) return { title: 'Post no encontrado' };
  return {
    title: `${post.title} — ChandeliERP Blog`,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: 'article',
      publishedTime: post.date,
      authors: [post.author],
    },
  };
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params;
  const post = getPostBySlug(slug);
  if (!post) notFound();

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-white">
        <article className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          {/* Post header */}
          <header className="mb-10">
            <div className="flex items-center gap-3 text-sm text-gray-400 mb-4">
              <time dateTime={post.date}>{post.date}</time>
              <span>&middot;</span>
              <span>{post.author}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight leading-tight">
              {post.title}
            </h1>
          </header>

          {/* MDX content */}
          <div className="prose prose-lg prose-pink max-w-none">
            <MDXRemote source={post.content} />
          </div>

          {/* Back link */}
          <div className="mt-12 pt-8 border-t border-gray-100">
            <a
              href="/blog"
              className="text-pink-600 font-medium hover:underline"
            >
              &larr; Volver al blog
            </a>
          </div>
        </article>
      </main>
      <Footer />
    </>
  );
}
