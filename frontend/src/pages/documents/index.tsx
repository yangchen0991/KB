import Head from 'next/head'
import { useState } from 'react'
import MainLayout from '../../components/Layout/MainLayout'

export default function Documents() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [documents] = useState([
    {
      id: 1,
      title: 'API 设计指南',
      category: 'development',
      size: '2.3 MB',
      uploadDate: '2024-01-15',
      author: '张三',
      tags: ['API', '设计', '开发']
    },
    {
      id: 2,
      title: '项目需求文档',
      category: 'project',
      size: '1.8 MB',
      uploadDate: '2024-01-14',
      author: '李四',
      tags: ['需求', '项目', '规划']
    },
    {
      id: 3,
      title: 'React 最佳实践',
      category: 'development',
      size: '3.1 MB',
      uploadDate: '2024-01-13',
      author: '王五',
      tags: ['React', '前端', '最佳实践']
    }
  ])

  const categories = [
    { id: 'all', name: '全部', count: documents.length },
    { id: 'development', name: '开发文档', count: documents.filter(d => d.category === 'development').length },
    { id: 'project', name: '项目文档', count: documents.filter(d => d.category === 'project').length }
  ]

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <>
      <Head>
        <title>文档管理 - 知识库系统</title>
        <meta name="description" content="管理和浏览知识库文档" />
      </Head>

      <MainLayout>
        <div className="p-6 space-y-6">
          {/* 页面标题和操作 */}
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
                  文档管理
                </h1>
                <p className="mt-2 text-gray-600">管理和浏览您的知识库文档</p>
              </div>
              <div className="mt-4 sm:mt-0">
                <button className="liquid-button px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-medium hover:shadow-lg transition-all duration-200">
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 bg-white rounded-sm opacity-90"></div>
                    <span>上传文档</span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* 搜索和筛选 */}
          <div className="glass-card p-6 rounded-2xl">
            <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
              {/* 搜索框 */}
              <div className="flex-1">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <div className="w-5 h-5 border-2 border-gray-400 rounded-full"></div>
                  </div>
                  <input
                    type="text"
                    placeholder="搜索文档..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl glass-input focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* 分类筛选 */}
              <div className="flex space-x-2">
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                      selectedCategory === category.id
                        ? 'bg-indigo-100 text-indigo-700 border-2 border-indigo-200'
                        : 'glass-card text-gray-600 hover:text-indigo-600 liquid-button'
                    }`}
                  >
                    {category.name} ({category.count})
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 文档列表 */}
          <div className="glass-card rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                文档列表 ({filteredDocuments.length})
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      文档名称
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      分类
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      大小
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      上传日期
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      作者
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white/50 divide-y divide-gray-200">
                  {filteredDocuments.map((document) => (
                    <tr key={document.id} className="hover:bg-blue-50/50 transition-colors duration-200">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mr-3">
                            <div className="w-4 h-4 bg-white rounded-sm opacity-90"></div>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">{document.title}</div>
                            <div className="flex space-x-1 mt-1">
                              {document.tags.map((tag, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {document.category === 'development' ? '开发文档' : '项目文档'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {document.size}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {document.uploadDate}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {document.author}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button className="text-indigo-600 hover:text-indigo-900 liquid-button px-3 py-1 rounded-lg">
                          查看
                        </button>
                        <button className="text-green-600 hover:text-green-900 liquid-button px-3 py-1 rounded-lg">
                          下载
                        </button>
                        <button className="text-red-600 hover:text-red-900 liquid-button px-3 py-1 rounded-lg">
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredDocuments.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                  <div className="w-8 h-8 bg-gray-400 rounded-sm"></div>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">没有找到文档</h3>
                <p className="text-gray-500">尝试调整搜索条件或上传新文档</p>
              </div>
            )}
          </div>
        </div>
      </MainLayout>
    </>
  )
}