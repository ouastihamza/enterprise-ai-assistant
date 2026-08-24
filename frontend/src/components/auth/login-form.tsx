"use client";

import {
  useState,
  type FormEvent,
} from "react";
import axios from "axios";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
} from "lucide-react";
import { motion } from "framer-motion";

import { useAuth } from "../../hooks/use-auth";

export function LoginForm() {
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] =
    useState(false);
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!email.trim() || !password) {
      setError(
        "Enter your business email and password."
      );
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      await login({
        email: email.trim(),
        password,
      });
    } catch (requestError) {
      if (axios.isAxiosError(requestError)) {
        const backendMessage =
          requestError.response?.data?.detail;

        if (typeof backendMessage === "string") {
          setError(backendMessage);
        } else if (
          requestError.response?.status === 401
        ) {
          setError(
            "The email or password is incorrect."
          );
        } else if (!requestError.response) {
          setError(
            "Atlas could not reach the platform. Please try again shortly."
          );
        } else {
          setError(
            "Authentication failed. Please try again."
          );
        }
      } else {
        setError(
          "Authentication failed. Please try again."
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="login-form"
      onSubmit={handleSubmit}
      noValidate
    >
      <div className="form-field">
        <label htmlFor="email">
          Business email
        </label>

        <div className="input-shell">
          <Mail
            size={18}
            strokeWidth={1.8}
            aria-hidden="true"
          />

          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            disabled={isSubmitting}
          />
        </div>
      </div>

      <div className="form-field">
        <div className="form-field__header">
          <label htmlFor="password">
            Password
          </label>

          <button
            className="text-button"
            type="button"
          >
            Forgot password?
          </button>
        </div>

        <div className="input-shell">
          <LockKeyhole
            size={18}
            strokeWidth={1.8}
            aria-hidden="true"
          />

          <input
            id="password"
            name="password"
            type={
              showPassword ? "text" : "password"
            }
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            disabled={isSubmitting}
          />

          <button
            className="password-toggle"
            type="button"
            aria-label={
              showPassword
                ? "Hide password"
                : "Show password"
            }
            onClick={() =>
              setShowPassword((value) => !value)
            }
          >
            {showPassword ? (
              <EyeOff size={18} />
            ) : (
              <Eye size={18} />
            )}
          </button>
        </div>
      </div>

      <div
        className={`form-error ${
          error ? "form-error--visible" : ""
        }`}
        role="alert"
        aria-live="polite"
      >
        {error}
      </div>

      <motion.button
        className="primary-button"
        type="submit"
        disabled={isSubmitting}
        whileHover={
          isSubmitting
            ? undefined
            : { y: -2, scale: 1.01 }
        }
        whileTap={
          isSubmitting
            ? undefined
            : { scale: 0.985 }
        }
      >
        <span>
          {isSubmitting
            ? "Opening workspace"
            : "Enter Atlas"}
        </span>

        {isSubmitting ? (
          <span className="button-loader" />
        ) : (
          <ArrowRight
            size={19}
            strokeWidth={1.8}
          />
        )}
      </motion.button>

      <p className="login-form__security">
        Protected by encrypted authentication and
        workspace-level access controls.
      </p>
    </form>
  );
}
