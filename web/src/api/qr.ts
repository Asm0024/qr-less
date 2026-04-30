import { BASE_URL } from "@/globals"
import { logout } from "./auth"
import { queryClient } from "@/query"

interface GenerateQRResponse {
	qr: string
	userId: string
	content: string
}

interface GenerateQRError {
	error: string
}

interface GenerateQRParams {
	content: string
	upload?: boolean
}

export async function generateQR({ content, upload = false }: GenerateQRParams): Promise<GenerateQRResponse> {
	const response = await fetch(BASE_URL + '/generate', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${localStorage.getItem('token')}`
		},
		body: JSON.stringify({ content, upload })
	})

	const data = await response.json()

	if (!response.ok) {
		const error = data as GenerateQRError
		if (error.error.includes('token')) {
			logout();
			queryClient.invalidateQueries({ queryKey: ['user'] })
		}
		throw new Error(error.error || 'Failed to generate QR code')
	}

	return data as GenerateQRResponse
}
