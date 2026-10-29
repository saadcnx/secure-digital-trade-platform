import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(err, info) {
    console.error(err, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="container page">
          <h2>Kuch ghalat ho gaya</h2>
          <p className="muted" style={{ margin: "8px 0 16px" }}>{this.state.error.message}</p>
          <button className="btn" onClick={() => window.location.reload()}>Reload</button>
        </div>
      );
    }
    return this.props.children;
  }
}