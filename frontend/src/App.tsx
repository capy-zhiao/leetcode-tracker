// Route table: which URL renders which page.
// ":number" is a dynamic segment — /solve/994 passes "994" to the Solve page.
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
