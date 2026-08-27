import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/AppShell'
import { Landing } from '@/routes/Landing'
import { Orcamento } from '@/routes/Orcamento'
import { Revisao } from '@/routes/Revisao'

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Landing />} />
        <Route path="revisao" element={<Revisao />} />
        <Route path="orcamento" element={<Orcamento />} />
      </Route>
    </Routes>
  )
}
