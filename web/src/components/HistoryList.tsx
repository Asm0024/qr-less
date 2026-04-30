import { useQuery } from '@tanstack/react-query'
import { getHistory } from '@/api/history'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QRShareActions } from '@/components/QRShareActions'

export function HistoryList() {
	const {
		data: historyData,
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ['history'],
		queryFn: getHistory,
	})

	if (isLoading) return <div>Loading history...</div>

	if (isError) {
		return (
			<div>
				Error: {error instanceof Error ? error.message : 'Failed to load history.'}
			</div>
		)
	}

	if (!historyData || historyData.history.length === 0) {
		return (
			<div className="text-center text-slate-500">
				You have not generated any QR codes yet.
			</div>
		)
	}

	return (
		<div className="space-y-4">
			<h2 className="text-2xl font-bold text-center">History</h2>
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{historyData.history.map(item => (
					<Card key={item.content + item.createdAt}>
						<CardHeader>
							<CardTitle>{item.content.slice(0, 20)} {item.content.length > 20 && '...'}</CardTitle>
						</CardHeader>
						<CardContent className="flex flex-col items-center">
							<img src={item.qrCode} alt={`QR code for ${item.content}`} className="w-40 h-40" />
							<p className="text-sm text-slate-500 mt-2">
								{new Date(item.createdAt).toLocaleString()}
							</p>
							<div className="mt-4">
								<QRShareActions
									qrCode={item.qrCode}
									content={item.content}
									imageUrl={isUrl(item.qrCode) ? item.qrCode : null}
									compact
								/>
							</div>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	)
}

function isUrl(text: string) {
	try {
		new URL(text)
		return true
	} catch {
		return false
	}
}
