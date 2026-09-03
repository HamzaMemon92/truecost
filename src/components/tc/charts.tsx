import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = { label: string; value: number };

const axisStyle = {
  fontSize: 11,
  fill: "var(--color-muted-foreground)",
};

function TipBox({ active, payload, label, format }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-2.5 py-1.5 shadow-[var(--shadow-pop)]">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="tc-num text-xs font-bold text-foreground">
        {format ? format(payload[0].value) : payload[0].value}
      </p>
    </div>
  );
}

export function TrendArea({
  data,
  height = 180,
  format,
  showAxis = true,
  ticks,
}: {
  data: Point[];
  height?: number;
  format?: (n: number) => string;
  showAxis?: boolean;
  ticks?: string[];
}) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 6, right: 6, bottom: 0, left: showAxis ? -12 : -40 }}>
          <defs>
            <linearGradient id="tcArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity={0.22} />
              <stop offset="100%" stopColor="var(--color-brand)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={showAxis ? axisStyle : false}
            interval="preserveStartEnd"
            minTickGap={28}
            tickFormatter={(v, i) => (ticks ? (ticks[Math.round((i / (data.length - 1)) * (ticks.length - 1))] ?? "") : v)}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={showAxis ? axisStyle : false}
            width={showAxis ? 44 : 0}
            domain={["dataMin - 2%", "dataMax + 2%"]}
            tickFormatter={(v) => (format ? format(v) : String(v))}
          />
          <Tooltip content={<TipBox format={format} />} cursor={{ stroke: "var(--color-border)" }} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="var(--color-brand)"
            strokeWidth={2}
            fill="url(#tcArea)"
            dot={false}
            activeDot={{ r: 3.5, strokeWidth: 2, stroke: "var(--color-card)" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TrendBars({
  data,
  height = 200,
  format,
}: {
  data: Point[];
  height?: number;
  format?: (n: number) => string;
}) {
  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 6, right: 6, bottom: 0, left: -12 }} barCategoryGap="30%">
          <defs>
            <linearGradient id="tcBar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity={0.95} />
              <stop offset="100%" stopColor="var(--color-brand)" stopOpacity={0.45} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={axisStyle} />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={axisStyle}
            width={44}
            tickFormatter={(v) => (format ? format(v) : String(v))}
          />
          <Tooltip
            content={<TipBox format={format} />}
            cursor={{ fill: "var(--color-muted)", opacity: 0.5 }}
          />
          <Bar dataKey="value" fill="url(#tcBar)" radius={[6, 6, 0, 0]} maxBarSize={34} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Donut({
  data,
  size = 150,
}: {
  data: { label: string; value: number; color: string }[];
  size?: number;
}) {
  return (
    <div style={{ height: size, width: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius="66%"
            outerRadius="100%"
            paddingAngle={2}
            stroke="none"
          >
            {data.map((d) => (
              <Cell key={d.label} fill={d.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Sparkline({ data, tone = "brand" }: { data: Point[]; tone?: "brand" | "danger" | "amber" | "positive" | "info" }) {
  const strokeMap = {
    brand: "var(--color-brand)",
    danger: "var(--color-danger)",
    amber: "var(--color-amber)",
    positive: "var(--color-positive)",
    info: "var(--color-info)",
  };
  const stroke = strokeMap[tone];
  const gradId = `spark-${tone}`;
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity={0.28} />
              <stop offset="100%" stopColor={stroke} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={stroke}
            strokeWidth={1.75}
            fill={`url(#${gradId})`}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
