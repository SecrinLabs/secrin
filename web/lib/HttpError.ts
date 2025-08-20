export function getFriendlyErrorMessage(
  status: number,
  defaultMessage: string
): string {
  switch (status) {
    case 400:
      return "The request was invalid. Please check your input.";
    case 401:
      return "You are not authorized. Please log in.";
    case 403:
      return "You don't have permission to access this resource.";
    case 404:
      return "The resource you are looking for was not found.";
    case 408:
      return "The request timed out. Please try again.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 500:
      return "Something went wrong on the server. Please try later.";
    case 503:
      return "The service is temporarily unavailable. Please try again soon.";
    default:
      return (
        defaultMessage || "An unexpected error occurred. Please try again."
      );
  }
}
