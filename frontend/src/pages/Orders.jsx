import { Link } from "react-router-dom";
import { api } from "../api";
import { useApp } from "../state";
import { Badge, Empty, ErrorBox, Loading, fdate, money, useLoad } from "../components/ui";

export default function Orders() {
  const { user } = useApp();
  const list = useLoad(() => api("/orders", { params: { limit: 100 } }), []);
  const mine = list.data?.filter((o) => o.buyer_id === user.id);

  return (
    <div className="container page">
      <h2>My orders</h2>
      {list.loading && !list.data ? (
        <Loading />
      ) : list.error ? (
        <ErrorBox error={list.error} onRetry={list.reload} />
      ) : !mine?.length ? (
        <Empty icon="📦" title="No orders yet"><Link className="btn" to="/">Start shopping</Link></Empty>
      ) : (
        <div className="card">
          {mine.map((o) => (
            <Link to={`/orders/${o.id}`} className="line" style={{ gridTemplateColumns: "1fr auto auto" }} key={o.id}>
              <div>
                <b>Order #{o.id}</b>
                <div className="muted sm">{fdate(o.created_at)} · {o.items.length} item{o.items.length === 1 ? "" : "s"}</div>
                <div className="muted sm">{o.items.map((i) => i.name).join(", ")}</div>
              </div>
              <div>
                <Badge s={o.status} />
                {o.on_hold && <Badge s="review">on hold</Badge>}
              </div>
              <b>{money(o.total, o.currency)}</b>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}