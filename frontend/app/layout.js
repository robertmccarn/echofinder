import "./globals.css";

export const metadata = {
  title: "EchoFinder",
  description: "Find modern echoes of legacy artists."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
