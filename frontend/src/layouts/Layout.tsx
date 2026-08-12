import { Outlet } from "react-router-dom";
import { Lock } from "lucide-react";

export function Layout() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F5F8FC' }}>
      <header style={{ 
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        height: '72px',
        padding: '0 2rem',
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
      }}>
        
        {/* LEFT: Logo & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '48px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <img src="/logo.png" alt="NETI Logo" style={{ width: '40px', height: '40px', objectFit: 'contain' }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <h1 style={{ margin: 0, fontSize: '1.25rem', color: '#0F172A', fontWeight: 800, lineHeight: 1.1 }}>NETI</h1>
              <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 700, letterSpacing: '0.05em' }}>
                NON-EXPLOITABLE<br/>TEST INTEGRITY
              </span>
            </div>
          </div>
          
          <div className="header-exam-title" style={{ display: 'flex', alignItems: 'center', paddingLeft: '24px', borderLeft: '1px solid #E2E8F0', height: '40px' }}>
             <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
                <span style={{ fontSize: '14px', color: '#0F172A', fontWeight: 600 }}>National Eligibility cum Entrance Test (NEET)</span>
             </div>
          </div>
        </div>

        {/* RIGHT: Session Info */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          border: '1px solid #E2E8F0',
          borderRadius: '8px',
          padding: '6px 16px',
          gap: '16px',
          backgroundColor: '#FFFFFF',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#16A34A', marginTop: '-12px' }}></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 500 }}>Secure Session</span>
              <span style={{ fontSize: '12px', color: '#16A34A', fontWeight: 600 }}>Connected</span>
            </div>
          </div>
          
          <div style={{ width: '1px', height: '28px', backgroundColor: '#E2E8F0' }}></div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F8FAFC', borderRadius: '4px', border: '1px solid #E2E8F0' }}>
              <Lock size={12} color="#64748B" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 500 }}>Session ID</span>
              <span style={{ fontSize: '12px', color: '#0F172A', fontWeight: 600 }}>NETI26-8F3A-91D2</span>
            </div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2.5rem 1.5rem 6rem', position: 'relative' }}>
        <Outlet />
      </main>
    </div>
  );
}
