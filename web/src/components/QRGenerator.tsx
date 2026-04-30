import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Link2, QrCode } from 'lucide-react';
import { toast } from '@/components/ui/sonner';
import { useMutation } from '@tanstack/react-query';
import { generateQR } from '@/api/qr';
import { queryClient } from '@/query';
import { QRShareActions } from '@/components/QRShareActions';

export function QRGenerator() {
  const [content, setContent] = useState('');
  const [uploadToS3, setUploadToS3] = useState(false);
  const [generatedQR, setGeneratedQR] = useState<string | null>(null);
  const [s3Url, setS3Url] = useState<string | null>(null);
  const [lastContent, setLastContent] = useState('');

  const generateQRMutation = useMutation({
    mutationFn: (params: { content: string; upload: boolean }) => generateQR(params),
    onSuccess: (data) => {
      setLastContent(data.content);
      if (isBase64Image(data.qr)) {
        setGeneratedQR(data.qr);
        setS3Url(null);
      } else if (isUrl(data.qr)) {
        setS3Url(data.qr);
        setGeneratedQR(data.qr);
      } else {
        setGeneratedQR(data.qr);
        setS3Url(null);
      }
      toast.success('Success', {
        description: uploadToS3 ? "QR code generated and uploaded to S3!" : "QR code generated successfully!",
      });
      queryClient.invalidateQueries({ queryKey: ['history'] })
    },
    onError: (error) => {
      console.error('QR generation error:', error);
      toast.error('Error', {
        description: error instanceof Error ? error.message : "Failed to generate QR code. Please try again.",
      });
    }
  });

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!content.trim()) {
      toast.error('Error', {
        description: "Please enter content for the QR code",
      });
      return;
    }

    generateQRMutation.mutate({
      content: content.trim(),
      upload: uploadToS3
    });
  };

  const isUrl = (text: string) => {
    try {
      new URL(text);
      return true;
    } catch {
      return false;
    }
  };

  const isBase64Image = (text: string) => {
    return text.startsWith('data:image/');
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <QrCode className="h-5 w-5" />
          QR Code Generator
        </CardTitle>
        <CardDescription>
          Generate QR codes from URLs, text, or numbers with optional AWS S3 upload
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleGenerate} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter URL, text, or number for QR code..."
              className="min-h-[100px]"
              required
            />
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="upload-s3"
              checked={uploadToS3}
              onCheckedChange={setUploadToS3}
            />
            <Label htmlFor="upload-s3">Upload to AWS S3</Label>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={generateQRMutation.isPending}
          >
            {generateQRMutation.isPending ? 'Generating...' : 'Generate QR Code'}
          </Button>
        </form>

        {generatedQR && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold">Generated QR Code</h3>
            <div className="border rounded-lg p-4 bg-muted/50">
              {isBase64Image(generatedQR) && (
                <img
                  src={generatedQR}
                  alt="Generated QR Code"
                  className="max-w-full h-auto mx-auto"
                />
              )}
              {s3Url && (
                <div className="mt-4 text-center">
                  <p className="mb-2">QR code uploaded to S3:</p>
                  <img
                    src={generatedQR}
                    alt="Generated QR Code"
                    className="max-w-full h-auto mx-auto"
                  />
                  <a
                    href={s3Url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline break-all"
                  >
                    {s3Url}
                  </a>
                </div>
              )}
              {!isBase64Image(generatedQR) && !s3Url && (
                <div className="text-center">
                  <p className="font-mono text-sm break-all">{generatedQR}</p>
                </div>
              )}

              <div className="mt-6 space-y-3 border-t pt-4">
                <QRShareActions qrCode={generatedQR} content={lastContent} imageUrl={s3Url} />

                {s3Url && (
                  <div className="flex items-center gap-2 rounded-md bg-background p-2 text-sm text-muted-foreground">
                    <Link2 className="h-4 w-4 shrink-0" />
                    <span className="break-all">{s3Url}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
