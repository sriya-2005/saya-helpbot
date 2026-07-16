// A small component whose only job is to show 3 bouncing dots,
// like "..." — telling the user "the bot is thinking."
// It takes no inputs (props) because it never changes.
export default function LoadingDots() {
  return (
    <div className="loading-dots" aria-label="SAYA HelpBot is typing">
      <span></span>
      <span></span>
      <span></span>
    </div>
  )
}
