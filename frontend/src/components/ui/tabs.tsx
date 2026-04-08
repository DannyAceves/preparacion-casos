"use client";

import { ReactNode } from "react";

interface TabDefinition {
  key: string;
  label: string;
  badge?: string | number;
}

interface TabsProps {
  items: TabDefinition[];
  activeKey: string;
  onChange: (key: string) => void;
}

interface TabPanelProps {
  children: ReactNode;
}

export function Tabs({ items, activeKey, onChange }: TabsProps): JSX.Element {
  return (
    <div className="ui-tabs" role="tablist" aria-label="Case sections">
      {items.map((item) => {
        const isActive = item.key === activeKey;
        return (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={`ui-tab ${isActive ? "ui-tab--active" : ""}`}
            onClick={() => onChange(item.key)}
          >
            <span>{item.label}</span>
            {item.badge !== undefined ? <span className="ui-tab__badge">{item.badge}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({ children }: TabPanelProps): JSX.Element {
  return <div role="tabpanel">{children}</div>;
}
