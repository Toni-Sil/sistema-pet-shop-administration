import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLocation } from "react-router-dom";
import { Sparkles, X, Bot } from "lucide-react";
import { Button } from "./ui/button";

interface GuideState {
  selector: string;
  message: string;
  label: string;
}

export const AIGuide = () => {
  const location = useLocation();
  const [guide, setGuide] = useState<GuideState | null>(() => {
    const saved = localStorage.getItem("ai-active-guide");
    return saved ? JSON.parse(saved) : null;
  });
  const [coords, setCoords] = useState({ top: 0, left: 0 });

  useEffect(() => {
    const handleGuide = (e: any) => {
      const newState = { 
        selector: e.detail.selector, 
        message: e.detail.message, 
        label: e.detail.label 
      };
      setGuide(newState);
      localStorage.setItem("ai-active-guide", JSON.stringify(newState));
    };

    window.addEventListener("ai-guide-target", handleGuide as any);
    return () => window.removeEventListener("ai-guide-target", handleGuide as any);
  }, []);

  useEffect(() => {
    if (!guide) {
      localStorage.removeItem("ai-active-guide");
      return;
    }

    const updateCoords = () => {
      const el = document.querySelector(guide.selector);
      if (el) {
        const rect = el.getBoundingClientRect();
        setCoords({
          top: rect.top + rect.height / 2,
          left: rect.left + rect.width + 10,
        });
      }
    };

    updateCoords();
    const interval = setInterval(updateCoords, 200);
    return () => clearInterval(interval);
  }, [guide]);

  // Hide if element doesn't appear after 10 seconds of navigation
  useEffect(() => {
    if (!guide) return;
    const timeout = setTimeout(() => {
      if (!document.querySelector(guide.selector)) {
        setGuide(null);
        localStorage.removeItem("ai-active-guide");
      }
    }, 10000);
    return () => clearTimeout(timeout);
  }, [guide, location.pathname]); // Triggered on path change too

  const isVisible = guide && document.querySelector(guide.selector);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: -20, scale: 0.8 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: -20, scale: 0.8 }}
          className="fixed z-[100] flex items-center pointer-events-none drop-shadow-2xl"
          style={{ top: coords.top, left: coords.left, translateY: "-50%" }}
        >
          {/* Character */}
          <div className="absolute -left-16 bottom-0">
             <motion.div 
               animate={{ y: [0, -5, 0] }} 
               transition={{ repeat: Infinity, duration: 2 }}
               className="h-12 w-12 bg-primary rounded-full border-4 border-white shadow-lg flex items-center justify-center"
             >
                <Sparkles className="h-6 w-6 text-white" />
             </motion.div>
          </div>
          {/* Arrow */}
          <div className="w-0 h-0 border-y-[8px] border-y-transparent border-r-[10px] border-r-primary" />
          
          <div className="bg-primary text-primary-foreground p-3 rounded-2xl shadow-2xl max-w-[200px] pointer-events-auto border-2 border-primary-foreground/20">
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 animate-pulse" />
                <span className="text-[10px] font-black uppercase tracking-tighter opacity-80">Sugestão de IA</span>
              </div>
              <button onClick={() => setGuide(null)} className="hover:rotate-90 transition-transform">
                <X className="h-3 w-3" />
              </button>
            </div>
            
            <p className="text-[11px] leading-tight font-medium mb-2">{guide.message}</p>
            
            <Button 
              size="sm" 
              variant="secondary" 
              className="h-6 w-full text-[10px] font-black bg-white text-primary hover:bg-white/90 rounded-full"
              onClick={() => {
                const el = document.querySelector(guide.selector) as HTMLElement;
                if (el) el.click();
                setGuide(null);
              }}
            >
              {guide.label || "Ver agora"}
            </Button>
          </div>

          {/* Pulse effect on target */}
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: [1, 1.5, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="absolute -left-12 h-6 w-6 rounded-full border-2 border-primary opacity-50 pointer-events-none"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};
