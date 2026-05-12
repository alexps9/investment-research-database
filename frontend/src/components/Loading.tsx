import styles from './Loading.module.css';

interface LoadingProps {
  message?: string;
}

export default function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className={styles.loading} role="status" aria-live="polite">
      <p className={styles.message}>{message}</p>
    </div>
  );
}
