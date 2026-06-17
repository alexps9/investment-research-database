export function generateStaticParams() {
  return [{ id: 'placeholder' }];
}

export default function SessionLayout({ children }: { children: React.ReactNode }) {
  return children;
}
