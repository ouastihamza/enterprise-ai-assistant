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

import {
  registerRequest,
} from "../../services/auth.service";

import {
  getApiErrorMessage,
} from "../../lib/api";

export default function RegisterPage() {
  const router = useRouter();

  const {
    login,
    isAuthenticated,
    isLoading,
  } = useAuth();

  const [fullName, setFullName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState<string | null>(null);

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

    setError(null);
    setIsSubmitting(true);

    try {
      await registerRequest({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
      });

      await login({
        email: email.trim(),
        password,
      });

      router.replace("/dashboard");
    } catch (submitError) {
      setError(
        getApiErrorMessage(
          submitError,
          "Unable to create your account."
        )
      );
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
          A
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
              A
            </div>

            <div>
              <strong>ATLAS</strong>
              <span>
                Enterprise Intelligence
              </span>
            </div>
          </header>

          <div className="auth-brand-panel__content">
            <span className="auth-eyebrow">
              <Sparkles size={15} />
              Secure company intelligence
            </span>

            <h1>
              One clear view of every customer.
            </h1>

            <p>
              Bring customer details and documents together, then ask Atlas for clear, sourced answers.
            </p>

            <div className="auth-capabilities">
              <div>
                <ShieldCheck size={18} />

                <span>
                  <strong>
                    Customer data protected
                  </strong>

                  Each company sees only its own
                  information.
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
            ATLAS · Enterprise Intelligence
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

              <h2>Create your account</h2>

              <p>
                Set up your company&apos;s workspace
                access.
              </p>
            </div>

            <label className="auth-field">
              <span>Full name</span>

              <input
                type="text"
                value={fullName}
                onChange={(event) => {
                  setFullName(
                    event.target.value
                  );

                  if (error) {
                    setError(null);
                  }
                }}
                placeholder="Jane Doe"
                autoComplete="name"
                required
              />
            </label>

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
                    setError(null);
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
                    setError(null);
                  }
                }}
                placeholder="Create a password"
                autoComplete="new-password"
                minLength={8}
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
                  ? "Creating account..."
                  : "Create account"}
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
              Already have an account?{" "}
              <Link href="/login">
                Sign in
              </Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
