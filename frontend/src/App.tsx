// 路由表:哪个网址显示哪个页面。
// :number 是动态参数,比如 /solve/994 会把 "994" 传给 Solve 页面。
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Today from './pages/Today'
import Solve from './pages/Solve'
import Problems from './pages/Problems'
import Mock from './pages/Mock'
import Stats from './pages/Stats'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Today />} />
        <Route path="/solve/:number" element={<Solve />} />
        <Route path="/problems" element={<Problems />} />
        <Route path="/mock" element={<Mock />} />
        <Route path="/stats" element={<Stats />} />
      </Routes>
    </Layout>
  )
}
