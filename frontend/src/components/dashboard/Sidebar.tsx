"use client";

import { RiGraduationCapLine } from "react-icons/ri";
import {
  FiClock, FiFile, FiSettings, FiHelpCircle, FiLogOut,
  FiEdit2, FiTrash2, FiHome,
} from "react-icons/fi";
import { RiFileList2Line } from "react-icons/ri";
import { AiOutlineFolderAdd } from "react-icons/ai";
import { IoAddOutline } from "react-icons/io5";
import { GoSidebarCollapse, GoSidebarExpand } from "react-icons/go";
import { SlOptions } from "react-icons/sl";
import Link from "next/link";
import { useDashboardStore } from "@/src/store/dashboard.store";
import { useAuthStore } from "@/src/store/auth.store";
import { usePathname, useRouter } from "next/navigation";
import { LogoutModal } from "./LogoutModal";
import { useState, useRef, useEffect } from "react";
import { apiDeleteChat, apiUpdateChat } from "@/src/services/chat.service";

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}

const NAV_ITEMS = [
  { name: "Inicio",        path: "/dashboard",               icon: FiHome,            iconSize: "h-4 w-4" },
  { name: "Historial",     path: "/dashboard/historial",     icon: FiClock,           iconSize: "h-4 w-4" },
  { name: "Subir archivo", path: "/dashboard/subir-archivo", icon: AiOutlineFolderAdd,iconSize: "h-4 w-4" },
  { name: "Examenes",      path: "/dashboard/examenes",      icon: RiFileList2Line,   iconSize: "h-4 w-4" },
];
const NAV_BOTTOM = [
  { name: "Configuración",   path: "/dashboard/configuracion", icon: FiSettings,   iconSize: "h-4 w-4" },
  { name: "Centro de ayuda", path: "/dashboard/centro-ayuda",  icon: FiHelpCircle, iconSize: "h-4 w-4" },
];

export default function Sidebar({ collapsed, setCollapsed }: SidebarProps) {
  const router   = useRouter();
  const pathname = usePathname();
  const chats      = useDashboardStore((s) => s.chats);
  const deleteChat = useDashboardStore((s) => s.deleteChat);
  const updateChat = useDashboardStore((s) => s.updateChat);
  const logout     = useAuthStore((s) => s.logout);
  const token      = useAuthStore((s) => s.token);

  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [openMenuId,   setOpenMenuId]   = useState<string | null>(null);
  const [editingId,    setEditingId]    = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const menuRef = useRef<HTMLDivElement>(null);

  const filteredChats = chats.filter((c) => c.messages.length > 0);

  const handleLogoutConfirm = () => { logout(); setShowLogoutModal(false); router.push("/"); };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpenMenuId(null);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleRenameSubmit = async (chatId: string) => {
    if (!editingTitle.trim()) { setEditingId(null); return; }
    const chat = chats.find((c) => c.id === chatId);
    if (chat) {
      try { await apiUpdateChat(token, chat.backendId, editingTitle.trim()); updateChat(chatId, { title: editingTitle.trim() }); }
      catch (err) { console.error("Error al renombrar:", err); }
    }
    setEditingId(null); setEditingTitle("");
  };

  const handleDelete = async (chatId: string) => {
    const chat = chats.find((c) => c.id === chatId);
    if (chat) { try { await apiDeleteChat(token, chat.backendId); } catch (err) { console.error(err); } }
    deleteChat(chatId); setOpenMenuId(null);
    if (pathname === `/dashboard/chat/${chatId}`) router.push("/dashboard");
  };

  return (
    <>
      <LogoutModal isOpen={showLogoutModal} onConfirm={handleLogoutConfirm} onCancel={() => setShowLogoutModal(false)} />

      <div className={`hidden md:flex fixed left-0 top-0 h-screen bg-white border-r border-gray-200 flex-col transition-all duration-300 ease-in-out z-30 ${collapsed ? "w-16" : "w-52"}`}>

        <div className={`px-3 py-5 flex items-center ${collapsed ? "justify-center" : "justify-between gap-2"}`}>
          {collapsed ? (
            <div className="relative group">
              <RiGraduationCapLine className="h-8 w-8 text-white p-2 rounded bg-blue-950 shrink-0 group-hover:opacity-0 transition-opacity duration-150" />
              <button onClick={() => setCollapsed(false)} title="Expandir" className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-150 text-gray-500 hover:text-gray-800 bg-gray-100 rounded-lg">
                <GoSidebarCollapse className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 min-w-0">
                <RiGraduationCapLine className="h-8 w-8 text-white p-2 rounded bg-blue-950 shrink-0" />
                <span className="text-base font-bold text-indigo-900 tracking-tight truncate">SchoolAI</span>
              </div>
              <button onClick={() => setCollapsed(true)} className="text-gray-400 hover:text-gray-600 transition-colors shrink-0" title="Contraer">
                <GoSidebarExpand className="h-5 w-5" />
              </button>
            </>
          )}
        </div>

        <div className={`mb-4 ${collapsed ? "flex justify-center px-2" : "px-3"}`}>
          {collapsed ? (
            <button onClick={() => router.push("/dashboard")} className="w-10 h-10 flex items-center justify-center bg-blue-950 hover:bg-blue-900 text-white rounded-xl transition-colors" title="Nuevo chat">
              <IoAddOutline className="h-5 w-5" />
            </button>
          ) : (
            <button onClick={() => router.push("/dashboard")} className="w-full flex items-center gap-2 bg-blue-950 hover:bg-blue-900 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors">
              <IoAddOutline className="h-4 w-4 shrink-0" /> Nuevo chat
            </button>
          )}
        </div>

        <nav className={`space-y-0.5 ${collapsed ? "px-2" : "px-3"}`}>
          {NAV_ITEMS.filter((i) => i.path !== "/dashboard").map((item) => {
            const Icon = item.icon; const isActive = pathname === item.path;
            return collapsed ? (
              <Link key={item.path} href={item.path} title={item.name} className={`flex items-center justify-center w-10 h-10 mx-auto rounded-lg transition-colors ${isActive ? "bg-indigo-50 text-indigo-900" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"}`}>
                <Icon className={item.iconSize} />
              </Link>
            ) : (
              <Link key={item.path} href={item.path} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? "bg-indigo-50 text-indigo-900" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"}`}>
                <Icon className={item.iconSize} /><span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {!collapsed && (
          <div className="flex-1 overflow-y-auto px-3 mt-5 min-h-0" ref={menuRef}>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest px-3 mb-2">Chats recientes</p>
            <div className="space-y-0.5">
              {filteredChats.length === 0 && <p className="text-xs text-gray-300 px-3 py-1">Sin chats aún</p>}
              {filteredChats.map((chat) => {
                const isActive = pathname === `/dashboard/chat/${chat.id}`;
                const isEditing = editingId === chat.id;
                const isMenuOpen = openMenuId === chat.id;
                return (
                  <div key={chat.id} className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-colors ${isActive ? "bg-indigo-50 text-indigo-900" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"}`}>
                    {isEditing ? (
                      <input autoFocus value={editingTitle} onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleRenameSubmit(chat.id)}
                        onKeyDown={(e) => { if (e.key === "Enter") handleRenameSubmit(chat.id); if (e.key === "Escape") setEditingId(null); }}
                        className="flex-1 bg-white border border-blue-300 rounded px-2 py-0.5 text-xs text-gray-800 outline-none focus:ring-1 focus:ring-blue-400" />
                    ) : (
                      <>
                        <Link href={`/dashboard/chat/${chat.id}`} className="flex items-center gap-2 flex-1 min-w-0">
                          <FiFile className="h-3.5 w-3.5 shrink-0 opacity-60" />
                          <span className="truncate">{chat.title}</span>
                        </Link>
                        <button onClick={(e) => { e.preventDefault(); setOpenMenuId(isMenuOpen ? null : chat.id); }} className="opacity-0 group-hover:opacity-100 shrink-0 text-gray-400 hover:text-gray-600 transition-all p-0.5 rounded">
                          <SlOptions className="h-3 w-3" />
                        </button>
                        {isMenuOpen && (
                          <div className="absolute right-2 top-8 z-20 bg-white border border-gray-100 rounded-xl shadow-lg py-1 w-36">
                            <button onClick={() => { setEditingId(chat.id); setEditingTitle(chat.title); setOpenMenuId(null); }} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors">
                              <FiEdit2 className="h-3.5 w-3.5" /> Renombrar
                            </button>
                            <button onClick={() => handleDelete(chat.id)} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-red-50 transition-colors">
                              <FiTrash2 className="h-3.5 w-3.5" /> Eliminar
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {collapsed && <div className="flex-1" />}

        <div className={`mt-2 border-t border-gray-100 pt-3 pb-2 space-y-0.5 ${collapsed ? "px-2" : "px-3"}`}>
          {NAV_BOTTOM.map((item) => {
            const Icon = item.icon; const isActive = pathname === item.path;
            return collapsed ? (
              <Link key={item.path} href={item.path} title={item.name} className={`flex items-center justify-center w-10 h-10 mx-auto rounded-lg transition-colors ${isActive ? "bg-indigo-50 text-indigo-900" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"}`}>
                <Icon className={item.iconSize} />
              </Link>
            ) : (
              <Link key={item.path} href={item.path} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? "bg-indigo-50 text-indigo-900" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"}`}>
                <Icon className={item.iconSize} /><span>{item.name}</span>
              </Link>
            );
          })}
          {collapsed ? (
            <button onClick={() => setShowLogoutModal(true)} title="Cerrar sesión" className="flex items-center justify-center w-10 h-10 mx-auto rounded-lg text-white bg-blue-950 hover:bg-blue-900 transition-colors">
              <FiLogOut className="h-4 w-4" />
            </button>
          ) : (
            <button onClick={() => setShowLogoutModal(true)} className="w-full bg-blue-950 text-white hover:bg-blue-900 flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors">
              <FiLogOut className="h-4 w-4 shrink-0" /><span>Cerrar sesión</span>
            </button>
          )}
        </div>

        {/*<div className={`pb-4 pt-3 border-t border-gray-100 ${collapsed ? "flex justify-center px-2" : "px-3"}`}>
          {collapsed ? (
            <a
              href="https://www.softserveinc.com/"
              target="_blank"
              rel="noopener noreferrer"
              title="SoftServe"
              className="w-10 h-10 flex items-center justify-center bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <SoftServeLogo size={18} />
            </a>
          ) : (
            <a
              href="https://www.softserveinc.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2.5 w-full px-2 py-2 rounded-lg bg-gray-900 hover:bg-gray-800 transition-colors group"
            >
              <div className="w-6 h-5 flex items-center justify-center shrink-0">
                <SoftServeLogo size={22} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-xs font-light leading-none">SoftServe</p>
              </div>
            </a>
          )}
        </div>*/}

      </div>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-gray-200 flex items-center justify-around px-2 py-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.path;
          return (
            <Link key={item.path} href={item.path}
              className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-colors ${isActive ? "text-blue-950" : "text-gray-400"}`}>
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium truncate">{item.name}</span>
            </Link>
          );
        })}
        <button onClick={() => router.push("/dashboard")} className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl text-white bg-blue-950">
          <IoAddOutline className="h-5 w-5" />
          <span className="text-[10px] font-medium">Nuevo</span>
        </button>
        <Link href="/dashboard/configuracion"
          className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-colors ${pathname === "/dashboard/configuracion" ? "text-blue-950" : "text-gray-400"}`}>
          <FiSettings className="h-5 w-5" />
          <span className="text-[10px] font-medium">Ajustes</span>
        </Link>
      </nav>
    </>
  );
}
