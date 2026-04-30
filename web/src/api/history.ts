import { BASE_URL } from "@/globals"
import { logout } from "./auth"
import { queryClient } from "@/query"

interface HistoryItem {
	userId: string
	content: string
	createdAt: string
	qrCode: string // url or base64
}

interface HistoryResponse {
	history: HistoryItem[]
}

interface HistoryError {
	error: string
}

export async function getHistory(): Promise<HistoryResponse> {
	const response = await fetch(BASE_URL + '/history', {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${localStorage.getItem('token')}`
		},
	})

	const data = await response.json()

	if (!response.ok) {
		const error = data as HistoryError
		console.log(error)
		if (error.error.includes('token') || error.error.includes('expired')) {
			logout()
			queryClient.invalidateQueries({ queryKey: ['user'] })
		}
		throw new Error(error.error || 'Failed to fetch history')
	}

	return data as HistoryResponse
}

export type { HistoryItem, HistoryResponse } 