import { Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Dashboard } from './pages/Dashboard';
import { RecoveryCases } from './pages/RecoveryCases';
import { CaseDetail } from './pages/CaseDetail';
import { DemoMode } from './pages/DemoMode';
import { BatchProcessing } from './pages/BatchResults';
import { ApprovalQueue } from './pages/ApprovalQueue';
import { WebhookSimulator } from './pages/WebhookSimulator';
import { RoiCalculator } from './pages/RoiCalculator';
import { PolicyConfig } from './pages/PolicyConfig';

function App() {
  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#0B132B]">
      <Header />
      <main className="pb-16">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<RecoveryCases />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/webhooks" element={<WebhookSimulator />} />
          <Route path="/demo" element={<DemoMode />} />
          <Route path="/batch" element={<BatchProcessing />} />
          <Route path="/approval-queue" element={<ApprovalQueue />} />
          <Route path="/roi-calculator" element={<RoiCalculator />} />
          <Route path="/policy-config" element={<PolicyConfig />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
