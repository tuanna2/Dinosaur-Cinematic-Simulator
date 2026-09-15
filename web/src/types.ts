export interface RuntimeEnvironment {
  asset_id: string;
  weather: string;
  time_of_day: string;
}

export interface ActorInstance {
  instance_id: string;
  group_id: string;
  asset_id: string;
  species: string;
  variant?: string | null;
}

export interface CameraEvent {
  type: "camera";
  time: number;
  shot_id: string;
  end_time: number;
  camera: {
    preset: string;
    target?: string;
    lens_mm?: number;
  };
}

export interface ActionEvent {
  type: "action";
  time: number;
  shot_id: string;
  order: number;
  offset_seconds?: number;
  actor: string;
  resolved_instances: string[];
  action: string;
  target?: string | null;
  resolved_target_instances: string[];
  animation?: string | null;
}

export type RuntimeEvent = CameraEvent | ActionEvent;

export interface ExecutionPlan {
  plan_version: number;
  scenario_id: string;
  duration_seconds: number;
  style: string;
  environment: RuntimeEnvironment;
  actor_groups: Record<string, string[]>;
  instances: ActorInstance[];
  required_assets: string[];
  events: RuntimeEvent[];
  render: {
    width: number;
    height: number;
    fps: number;
    preview_scale: number;
  };
}

export interface AssetManifestEntry {
  id: string;
  web_path?: string | null;
}

export interface AssetManifest {
  assets: AssetManifestEntry[];
}
