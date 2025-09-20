import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="zh-CN">
      <Head>
        <meta charSet="utf-8" />
        <meta name="description" content="智能知识库管理系统" />
        <meta name="keywords" content="知识库,文档管理,搜索,分类,工作流" />
        <meta name="author" content="Knowledge Base Team" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="stylesheet" href="/styles/liquid-glass.css" />

        {/* 预加载字体 */}
        <link
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          as="style"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
