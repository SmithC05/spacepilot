export interface RouteData {
  destination: string;
  distance_m: number;
  duration_minutes: number;
  accessible: boolean;
  steps: string[];
}
