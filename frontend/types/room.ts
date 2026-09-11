export interface Room {
  room_id: string;
  name: string;
  capacity: number;
  projector: boolean;
  whiteboard: boolean;
  accessible: boolean;
  distance_m: number;
  available: boolean;
  isRecommended?: boolean;
  recommendationReason?: string;
}

export type BookingState = "idle" | "booking" | "confirmed" | "error";
