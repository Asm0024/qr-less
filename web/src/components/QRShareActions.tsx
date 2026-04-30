import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/sonner'
import { Copy, Image, Mail, MessageCircle, Send, Share2, Smartphone } from 'lucide-react'

interface QRShareActionsProps {
	qrCode: string
	content: string
	imageUrl?: string | null
	compact?: boolean
}

export function QRShareActions({ qrCode, content, imageUrl, compact = false }: QRShareActionsProps) {
	const shareText = content ? `QR code for: ${content}` : 'QR code'
	const shareLink = imageUrl || content || qrCode
	const size = compact ? 'icon' : 'default'

	const copyLink = async () => {
		await navigator.clipboard.writeText(shareLink)
		toast.success('Copied', {
			description: 'Share link copied to clipboard.',
		})
	}

	const shareNativeLink = async () => {
		if (!navigator.share) {
			await copyLink()
			return
		}

		await navigator.share({
			title: 'QR code',
			text: shareText,
			url: isUrl(shareLink) ? shareLink : undefined,
		})
	}

	const shareImage = async () => {
		let file: File

		try {
			file = await getQrImageFile(qrCode)
		} catch {
			toast.error('Could not load image', {
				description: 'Please try generating the QR code again.',
			})
			return
		}

		const shareData = {
			title: 'QR code',
			text: shareText,
			files: [file],
		}

		if (!navigator.canShare?.(shareData)) {
			toast.error('Image sharing is not supported here', {
				description: 'Use the copy or app link options instead.',
			})
			return
		}

		await navigator.share(shareData)
	}

	const labelClass = compact ? 'sr-only' : ''

	return (
		<div className={compact ? 'flex flex-wrap justify-center gap-2' : 'space-y-3'}>
			<div className={compact ? 'flex flex-wrap justify-center gap-2' : 'flex flex-col gap-2 sm:flex-row'}>
				<Button type="button" variant="secondary" size={size} onClick={copyLink} className={compact ? '' : 'flex-1'}>
					<Copy className="h-4 w-4" />
					<span className={labelClass}>Copy link</span>
				</Button>
				<Button type="button" variant="secondary" size={size} onClick={shareNativeLink} className={compact ? '' : 'flex-1'}>
					<Share2 className="h-4 w-4" />
					<span className={labelClass}>Share link</span>
				</Button>
				<Button type="button" variant="secondary" size={size} onClick={shareImage} className={compact ? '' : 'flex-1'}>
					<Image className="h-4 w-4" />
					<span className={labelClass}>Share image</span>
				</Button>
			</div>

			<div className={compact ? 'flex flex-wrap justify-center gap-2' : 'grid grid-cols-2 gap-2 sm:grid-cols-4'}>
				<ShareImageButton onClick={shareImage} compact={compact} label="Telegram">
					<Send className="h-4 w-4" />
				</ShareImageButton>
				<ShareImageButton onClick={shareImage} compact={compact} label="WhatsApp">
					<MessageCircle className="h-4 w-4" />
				</ShareImageButton>
				<ShareImageButton onClick={shareImage} compact={compact} label="SMS">
					<Smartphone className="h-4 w-4" />
				</ShareImageButton>
				<ShareImageButton onClick={shareImage} compact={compact} label="Email">
					<Mail className="h-4 w-4" />
				</ShareImageButton>
			</div>
		</div>
	)
}

function ShareImageButton({
	onClick,
	compact,
	label,
	children,
}: {
	onClick: () => void
	compact: boolean
	label: string
	children: React.ReactNode
}) {
	return (
		<Button type="button" variant="outline" size={compact ? 'icon' : 'sm'} onClick={onClick} title={`Share image with ${label}`}>
			{children}
			<span className={compact ? 'sr-only' : ''}>{label}</span>
		</Button>
	)
}

async function getQrImageFile(qrCode: string) {
	if (isBase64Image(qrCode)) {
		return dataUrlToFile(qrCode, 'qr-code.png')
	}

	const response = await fetch(qrCode)
	if (!response.ok) {
		throw new Error('Image could not be downloaded')
	}

	const blob = await response.blob()
	return new File([blob], 'qr-code.png', {
		type: blob.type || 'image/png',
	})
}

function dataUrlToFile(dataUrl: string, fileName: string) {
	const [header, base64Data] = dataUrl.split(',')
	const mime = header.match(/:(.*?);/)?.[1] || 'image/png'
	const bytes = atob(base64Data)
	const array = new Uint8Array(bytes.length)

	for (let i = 0; i < bytes.length; i += 1) {
		array[i] = bytes.charCodeAt(i)
	}

	return new File([array], fileName, { type: mime })
}

function isBase64Image(text: string) {
	return text.startsWith('data:image/')
}

function isUrl(text: string) {
	try {
		new URL(text)
		return true
	} catch {
		return false
	}
}
