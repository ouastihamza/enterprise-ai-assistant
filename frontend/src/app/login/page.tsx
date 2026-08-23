"use client";

import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  ArrowRight,
  Building2,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import Link from "next/link";

import {
  useRouter,
} from "next/navigation";

import {
  useAuth,
} from "../../hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();

  const {
    login,
    error,
    clearError,
    isAuthenticated,
    isLoading,
  } = useAuth();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  useEffect(() => {
    if (
      !isLoading &&
      isAuthenticated
    ) {
      router.replace("/dashboard");
    }
  }, [
    isAuthenticated,
    isLoading,
    router,
  ]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();

    clearError();
    setIsSubmitting(true);

    try {
      await login({
        email: email.trim(),
        password,
      });

      router.replace("/dashboard");
    } catch {
      // The authentication context displays
      // the backend error.
    } finally {
      setIsSubmitting(false);
    }
  }

  if (
    isLoading ||
    isAuthenticated
  ) {
    return (
      <main className="auth-loading-screen">
        <div className="auth-loading-screen__mark">
          V
        </div>

        <p>Preparing your workspace...</p>
      </main>
    );
  }

  return (
    <main className="auth-page">
      <div className="auth-page__background">
        <div className="auth-orb auth-orb--one" />
        <div className="auth-orb auth-orb--two" />
        <div className="auth-grid" />
      </div>

      <section className="auth-shell">
        <div className="auth-brand-panel">
          <header className="auth-brand">
            <div className="auth-brand__mark">
              V
            </div>

            <div>
              <strong>AI Agency</strong>
              <span>
                Enterprise AI Platform
              </span>
            </div>
          </header>

          <div className="auth-brand-panel__content">
            <span className="auth-eyebrow">
              <Sparkles size={15} />
              Secure company intelligence
            </span>

            <h1>
              Put your company&apos;s knowledge
              <span> into motion.</span>
            </h1>

            <p>
              Search internal documents, access
              trusted answers and collaborate with
              secure AI inside one isolated company
              workspace.
            </p>

            <div className="auth-capabilities">
              <div>
                <ShieldCheck size={18} />

                <span>
                  <strong>
                    Workspace isolated
                  </strong>

                  Company data remains separated by
                  workspace.
                </span>
              </div>

              <div>
                <Building2 size={18} />

                <span>
                  <strong>
                    Built for real teams
                  </strong>

                  Designed for controlled enterprise
                  usage.
                </span>
              </div>

              <div>
                <LockKeyhole size={18} />

                <span>
                  <strong>
                    Secure access
                  </strong>

                  Authenticated access to company
                  knowledge.
                </span>
              </div>
            </div>
          </div>

          <footer className="auth-brand-panel__footer">
            AI Agency · Enterprise AI Platform
          </footer>
        </div>

        <div className="auth-form-panel">
          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <div className="auth-form__heading">
              <span>
                Private workspace access
              </span>

              <h2>Welcome back</h2>

              <p>
                Sign in to continue to your company
                workspace.
              </p>
            </div>

            <label className="auth-field">
              <span>Email address</span>

              <input
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(
                    event.target.value
                  );

                  if (error) {
                    clearError();
                  }
                }}
                placeholder="name@company.com"
                autoComplete="email"
                required
              />
            </label>

            <label className="auth-field">
              <span>Password</span>

              <input
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(
                    event.target.value
                  );

                  if (error) {
                    clearError();
                  }
                }}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </label>

            {error ? (
              <div
                className="auth-form__error"
                role="alert"
              >
                {error}
              </div>
            ) : null}

            <button
              className="auth-submit"
              type="submit"
              disabled={isSubmitting}
            >
              <span>
                {isSubmitting
                  ? "Signing in..."
                  : "Enter workspace"}
              </span>

              {!isSubmitting ? (
                <ArrowRight size={18} />
              ) : null}
            </button>

            <p className="auth-form__security">
              <LockKeyhole size={14} />
              Protected enterprise access
            </p>

            <p className="auth-form__security">
              Don&apos;t have an account?{" "}
              <Link href="/register">
                Create one
              </Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
