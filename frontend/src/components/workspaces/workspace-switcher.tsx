"use client";

import {
  Building2,
  Check,
  ChevronsUpDown,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";

import { useWorkspace } from "../../hooks/use-workspace";

export function WorkspaceSwitcher() {
  const {
    activeWorkspace,
    workspaces,
    selectWorkspace,
  } = useWorkspace();

  const [isOpen, setIsOpen] = useState(false);
  const containerRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(
      event: MouseEvent
    ) {
      if (
        containerRef.current &&
        !containerRef.current.contains(
          event.target as Node
        )
      ) {
        setIsOpen(false);
      }
    }

    window.addEventListener(
      "mousedown",
      handleOutsideClick
    );

    return () => {
      window.removeEventListener(
        "mousedown",
        handleOutsideClick
      );
    };
  }, []);

  if (!activeWorkspace) {
    return null;
  }

  return (
    <div
      className="workspace-switcher"
      ref={containerRef}
    >
      <button
        type="button"
        className="workspace-switcher__trigger"
        onClick={() =>
          setIsOpen((current) => !current)
        }
        aria-expanded={isOpen}
      >
        <span className="workspace-switcher__icon">
          <Building2 size={17} />
        </span>

        <span className="workspace-switcher__identity">
          <strong>
            {activeWorkspace.company_name}
          </strong>
          <small>
            {activeWorkspace.industry ||
              "Company workspace"}
          </small>
        </span>

        <ChevronsUpDown size={15} />
      </button>

      {isOpen ? (
        <div className="workspace-switcher__menu">
          <span className="workspace-switcher__label">
            Company workspaces
          </span>

          {workspaces.map((workspace) => {
            const isSelected =
              workspace.id ===
              activeWorkspace.id;

            return (
              <button
                key={workspace.id}
                type="button"
                className={`workspace-switcher__option ${
                  isSelected
                    ? "workspace-switcher__option--active"
                    : ""
                }`}
                onClick={() => {
                  selectWorkspace(workspace.id);
                  setIsOpen(false);
                }}
              >
                <span className="workspace-switcher__avatar">
                  {workspace.company_name
                    .charAt(0)
                    .toUpperCase()}
                </span>

                <span>
                  <strong>
                    {workspace.company_name}
                  </strong>
                  <small>{workspace.name}</small>
                </span>

                {isSelected ? (
                  <Check size={15} />
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}