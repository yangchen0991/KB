import Head from 'next/head'
import { useState } from 'react'
import MainLayout from '../../components/Layout/MainLayout'

export default function Search() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    category: 'all',
    dateRange: 'all',
    fileType: 'all'
  })
  const [searchResults] = useState([
    {
      id: 1,
      title: 'React 组件设计模式',
      content: 'React 组件设计模式是前端开发中的重要概念，包括高阶组件、渲染属性、复合组件等...',
      category: 'development',
      author: '张三',
      date: '2024-01-15',
      relevance: 95
    },
    {
      id: 2,
      title: 'API 接口设计规范',
      content: 'RESTful API 设计规范包括资源命名、HTTP 方法使用、状态码定义等最佳实践...',
      category: 'development',
      author: '李四',
      date: '2024-01-14',
      relevance: 88
    },
    {
      id: 3,
      title: '项目管理流程指南',
      content: '敏捷开发流程管理，包括需求分析、迭代规划、代码审查、测试部署等环节...',
      category: 'project',
      author: '王五',
      date: '2024-01-13',
      relevance: 76
    }
  ])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // 这里会调用搜索 API
    console.log('搜索:', query, filters)
  }

  return (
    <>
      <Head>
        <title>智能搜索 - 知识库系统</title>
        <meta name="description" content="智能搜索知识库内容" />
      </Head>

      <MainLayout>
        <div className="p-6 space-y-6">
          {/* 搜索标题 */}
          <div className="glass-card p-6 rounded-2xl">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
              智能搜索
            </h1>
            <p className="mt-2 text-gray-600">快速查找您需要的知识和信息</p>
          </div>

          {/* 搜索表单 */}
          <div className="glass-card p-6 rounded-2xl">
            <form onSubmit={handleSearch} className="space-y-6">
              {/* 主搜索框 */}
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <div className="w-6 h-6 border-2 border-gray-400 rounded-full"></div>
                </div>
                <input
                  type="text"
                  placeholder="输入关键词搜索..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="block w-full pl-12 pr-4 py-4 text-lg border border-gray-200 rounded-xl glass-input focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  className="absolute inset-y-0 right-0 pr-4 flex items-center"
                >
                  <div className="liquid-button px-6 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg font-medium hover:shadow-lg transition-all duration-200">
                    搜索
                  </div>
                </button>
              </div>

              {/* 高级筛选 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">分类</label>
                  <select
                    value={filters.category}
                    onChange={(e) => setFilters({...filters, category: e.target.value})}
                    className="block w-full px-3 py-2 border border-gray-200 rounded-lg glass-input focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="all">全部分类</option>
                    <option value="development">开发文档</option>
                    <option value="project">项目文档</option>
                    <option value="design">设计文档</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">时间范围</label>
                  <select
                    value={filters.dateRange}
                    onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                    className="block w-full px-3 py-2 border border-gray-200 rounded-lg glass-input focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="all">全部时间</option>
                    <option value="week">最近一周</option>
                    <option value="month">最近一月</option>
                    <option value="year">最近一年</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">文件类型</label>
                  <select
                    value={filters.fileType}
                    onChange={(e) => setFilters({...filters, fileType: e.target.value})}
                    className="block w-full px-3 py-2 border border-gray-200 rounded-lg glass-input focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="all">全部类型</option>
                    <option value="pdf">PDF</option>
                    <option value="doc">Word</option>
                    <option value="txt">文本</option>
                  </select>
                </div>
              </div>
            </form>
          </div>

          {/* 搜索结果 */}
          {query && (
            <div className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  搜索结果 ({searchResults.length})
                </h2>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="w-4 h-4 bg-gray-400 rounded-sm"></div>
                  <span>按相关性排序</span>
                </div>
              </div>

              <div className="space-y-4">
                {searchResults.map((result) => (
                  <div key={result.id} className="glass-card p-6 rounded-xl liquid-hover group cursor-pointer">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                            {result.title}
                          </h3>
                          <div className="flex items-center space-x-1">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span className="text-sm text-green-600 font-medium">{result.relevance}% 匹配</span>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 mb-3 line-clamp-2">
                          {result.content}
                        </p>
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center space-x-1">
                            <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
                            <span>{result.author}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <div className="w-4 h-4 bg-gray-400 rounded-sm"></div>
                            <span>{result.date}</span>
                          </div>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {result.category === 'development' ? '开发文档' : '项目文档'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="ml-4 flex flex-col space-y-2">
                        <button className="liquid-button px-4 py-2 text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded-lg">
                          查看
                        </button>
                        <button className="liquid-button px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-200 rounded-lg">
                          收藏
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 分页 */}
              <div className="flex items-center justify-between mt-8">
                <div className="text-sm text-gray-500">
                  显示 1-{searchResults.length} 条，共 {searchResults.length} 条结果
                </div>
                <div className="flex space-x-2">
                  <button className="liquid-button px-4 py-2 text-gray-600 border border-gray-200 rounded-lg">
                    上一页
                  </button>
                  <button className="liquid-button px-4 py-2 bg-indigo-600 text-white rounded-lg">
                    1
                  </button>
                  <button className="liquid-button px-4 py-2 text-gray-600 border border-gray-200 rounded-lg">
                    下一页
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 搜索建议 */}
          {!query && (
            <div className="glass-card p-6 rounded-2xl">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">热门搜索</h2>
              <div className="flex flex-wrap gap-2">
                {['React 最佳实践', 'API 设计', '项目管理', '代码规范', '测试策略'].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(suggestion)}
                    className="liquid-button px-4 py-2 text-gray-600 hover:text-indigo-600 border border-gray-200 rounded-full"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </MainLayout>
    </>
  )
}