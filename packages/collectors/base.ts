export interface Collector {
  collect(): Promise<any>;
}
