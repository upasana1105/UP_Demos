// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, LogOut, Car, User } from 'lucide-react';
import Link from 'next/link';

export default function Navbar() {
  const [customerName, setCustomerName] = useState('');
  const [vehicleInfo, setVehicleInfo] = useState('');
  const router = useRouter();

  useEffect(() => {
    setCustomerName(localStorage.getItem('customer_name') || 'Policyholder');
    setVehicleInfo(localStorage.getItem('vehicle_info') || '');
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    router.push('/login');
  };

  return (
    <nav className="w-full bg-zinc-900/40 backdrop-blur-xl border-b border-zinc-800/80 px-6 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2.5 text-white hover:opacity-90">
          <div className="w-9 h-9 bg-indigo-600/10 border border-indigo-500/20 rounded-xl flex items-center justify-center text-indigo-400">
            <Shield size={18} />
          </div>
          <span className="font-bold tracking-tight text-base">Auto Claims</span>
        </Link>
        
        <div className="flex items-center gap-6">
          <div className="hidden sm:flex flex-col text-right">
            <div className="flex items-center gap-1.5 text-zinc-200 text-xs font-semibold justify-end">
              <User size={13} className="text-zinc-500" />
              <span>{customerName}</span>
            </div>
            {vehicleInfo && (
              <div className="flex items-center gap-1.5 text-zinc-500 text-[10px] justify-end mt-0.5">
                <Car size={11} />
                <span>{vehicleInfo}</span>
              </div>
            )}
          </div>
          
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-zinc-400 hover:text-white px-3.5 py-1.5 rounded-xl border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-950 active:scale-95 transition-all text-xs font-medium"
          >
            <LogOut size={13} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
